
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_cdcdf78997dba28f01ea7cff2a1d9b27 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_9ef139b72244a6c360b6f6a96142d508 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.vault_transfer", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 12px", ["borderRadius"] : "8px", ["background"] : "#818cf8", ["color"] : "#fff", ["fontSize"] : "12px", ["cursor"] : "pointer", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["opacity"] : "0.85" }) }),onClick:on_click_9ef139b72244a6c360b6f6a96142d508},children)
    )
});
