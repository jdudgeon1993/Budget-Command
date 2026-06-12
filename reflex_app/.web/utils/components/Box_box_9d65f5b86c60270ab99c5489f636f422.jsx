
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_9d65f5b86c60270ab99c5489f636f422 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_8037a5cb9c7899aa4b2eed37a3d14c02 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_show_archived_cats", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#6868a2", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["&:hover"] : ({ ["color"] : "#8282a2" }) }),onClick:on_click_8037a5cb9c7899aa4b2eed37a3d14c02},children)
    )
});
