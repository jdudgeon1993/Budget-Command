
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_eedf58854d5a99baca0ae6f99a15e9f9 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_8037a5cb9c7899aa4b2eed37a3d14c02 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.toggle_show_archived_cats", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#606088", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["&:hover"] : ({ ["color"] : "#9090B8" }) }),onClick:on_click_8037a5cb9c7899aa4b2eed37a3d14c02},children)
    )
});
